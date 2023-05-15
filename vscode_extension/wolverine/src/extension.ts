import {
	ExtensionContext,
	workspace,
	Position,
	TextEditor,
	Range,
	commands,
	window,
	TextDocument,
	CancellationTokenSource,
} from 'vscode';
import axios from 'axios';

// Flush interval is 30 milliseconds, because that's what the author found works well on the author's system.
// Ryzen 5900x + arch linux (btw)
const FLUSH_INTERVAL_MS = 5;

const countCharacters = (text: string) => text.replace(/\n/g, '').length;
const countNewLines = (text: string) => text.match(/\n/g)?.length || 0;
const getNewCursorLocation = (textStream: string, currentLine: number, currentCharacter: number): { newCharacterLocation: number, newLineLocation: number } => {
	const numberOfNewLines = countNewLines(textStream);
	const newCharacterLocation = numberOfNewLines === 0 ? countCharacters(textStream) + currentCharacter : 0;
	const newLineLocation = numberOfNewLines + currentLine;
	return { newCharacterLocation, newLineLocation };
};
const deleteRange = async (activeEditor: TextEditor, range: Range) => {
	await activeEditor.edit(editBuilder => {
		editBuilder.delete(range);
	});
};
// Gets the currently visible text, and if anything is folded, add ... 
const getVisibleText = async (document: TextDocument, visibleRanges: readonly Range[]): Promise<string> => {
	let visibleText = '';
	let lastVisibleRangeEnd: Position | null = null;

	visibleRanges.forEach((range, index) => {
		if (lastVisibleRangeEnd && document.offsetAt(range.start) - document.offsetAt(lastVisibleRangeEnd) > 1) {
			visibleText += '...';
		}
		visibleText += document.getText(range);
		lastVisibleRangeEnd = range.end;
	});

	return visibleText;
};
// See https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events
// Responsiblity of caller to register event listener.
const streamCompletion = async (prompt: string, onDataFunction: (chunk: any) => void, cancelFunction: (source: any, reject: () => void) => void): Promise<void> => {
	const openaikey = await workspace.getConfiguration().get('wolverine.UNSAFE.OpenaiApiKeySetting') || '';
	const messages: any[] = [
		{ role: 'user', content: prompt }
	];
	const headers = {
		['Content-Type']: 'application/json',
		['Authorization']: `Bearer ${openaikey}`,
	};

	const configurationModel = await workspace.getConfiguration().get('wolverine.model');
	const data = {
		'model': configurationModel || 'gpt-3.5-turbo',
		'messages': messages,
		'temperature': 0.1,
		'stream': true,
	};
	return new Promise(async (resolve, reject) => {
		const cancelSource = axios.CancelToken.source();
		const response = await axios({
			method: 'post',
			url: 'https://api.openai.com/v1/chat/completions',
			headers: headers,
			data: data,
			responseType: 'stream',
			cancelToken: cancelSource.token,
		});
		cancelFunction(cancelSource, resolve);
		response.data.on('data', onDataFunction);
		response.data.on('end', () => {
			resolve();
		});
	});
};

// Yacine threw most of the complexity into here.
// Holds a buffer in a javascript array, registers a event listener on a server-sent events function, builds the buffer
// Takes a position, and flushes the buffer on a preconfigured cron into the provided cursor position.
const useBufferToUpdateTextContentsWhileStreamingOpenAIResponse = async (activeEditor: TextEditor, position: Position, prompt: string, cancellationTokenSource: CancellationTokenSource): Promise<void> => {
	let currentCharacter = position.character;
	let currentLine = position.line;
	let buffer: string[] = [];
	let doneStreaming = false;
	// Triggered on data response from openai
	const onDataFunction = (word: any) => {
		const newContent = word.toString().split('data: ')
			.map((line: string) => line.trim())
			.filter((line: string) => line.length > 0)
			.map((line: string) => JSON.parse(line).choices[0].delta.content);
		buffer = [...buffer, ...newContent];
	};
	// Triggered when the cancellationTokenSource is invoked
	const cancelFunction = (source: any, resolve: any) => {
		cancellationTokenSource.token.onCancellationRequested(() => {
			doneStreaming = true;
			source.cancel();
			resolve();
		});
	};

	streamCompletion(prompt, onDataFunction, cancelFunction).then(() => doneStreaming = true);

	// While there is still data streaming or there is data in the buffer
	// Shift data from buffer and add to the text editor
	// Update currentCharacter and currentLine with the new cursor location
	// Wait for the specified flush interval before processing the next data
	while (!doneStreaming || buffer.length >= 0) {
		const word: string | undefined = buffer.shift();
		if (word) {
			let { newCharacterLocation, newLineLocation } = getNewCursorLocation(word, currentLine, currentCharacter);
			const position = new Position(currentLine, currentCharacter);
			await activeEditor.edit((editBuilder) => {
				editBuilder.insert(position, word);
			});
			currentCharacter = newCharacterLocation;
			currentLine = newLineLocation;
		}
		await sleep(FLUSH_INTERVAL_MS);
	}

	return;
};
const directedHealPrompt = async (text: string, filepath: string): Promise<string> => {
	const defaultInstructions = `
- The text under 'CODE' has come straight from my text editor. 
- Your entire output MUST be valid code.
- You may communicate back, but they MUST be in comments
- The code sent to you might have some instructions under comments. Follow the instructions. Only attend to instructions contained between [[SELECTED]] & [[/SELECTED]]
- The code between [[SELECTED]] [[/SELECTED]] is the ONLY code that you should replace. So when you start responding, only respond with code that should replace it, and nothing else.
- MAKE SURE YOU ONLY WRITE CODE TO REPLACE WHATS BETWEEN [[SELECTED]] AND [[/SELECTED]]. The rest of it doesnt need to be replaced
- The rest of the code is ONLY provided as context. Sometimes, I'll collapse my code for you, and hide the details under '...'. Follow the style of the rest of the provided code.
- DO NOT WRITE THE ENTIRE CODE FILE. ONLY REPLACE WHAT IS NECESSARY IN SELECTED
- Prefer functional programming principles.
`;
	const configurationInstructions = await workspace.getConfiguration().get('wolverine.prompt');
	return `
ADDITIONAL CONTEXT:
filepath: ${filepath}
INSTRUCTIONS:
${configurationInstructions || defaultInstructions}
CODE:
${text}
NEW CODE TO REPLACE WHAT IS BETWEEN [[SELECTED]] and [/SELECTED]:
`;
};

export async function activate(context: ExtensionContext) {
	let cancellationTokenSource: any = undefined;
	const directedHealDisposable = commands.registerCommand('wolverine.directedHeal', async () => {
		commands.executeCommand('setContext', 'wolverine.operationRunning', true);
		cancellationTokenSource = new CancellationTokenSource();

		const activeEditor = window.activeTextEditor;
		if (!activeEditor) {
			window.showErrorMessage('No text editor is currently active.');
			return;
		}

		const selection = activeEditor.selection;
		if (selection.isEmpty) {
			window.showErrorMessage('No text selected.');
			return;
		}

		const document = activeEditor.document;
		const visibleText = await getVisibleText(document, activeEditor.visibleRanges);

		// Get the selected text and replace it with marked selected text in the unfolded text
		// This should then be used in the prompt; to instruct the LLM what to do
		const selectedText = document.getText(selection);
		const contextText = visibleText.replace(selectedText, '[[SELECTED]]\n' + selectedText + '\n[[/SELECTED]]');
		const filePath = workspace.asRelativePath(document.uri);
		const prompt = await directedHealPrompt(contextText, filePath);

		// Determine the range to delete and replace
		const range: Range = new Range(selection.start, selection.end);
		await deleteRange(activeEditor, range);

		// Update the text using OpenAI response
		await useBufferToUpdateTextContentsWhileStreamingOpenAIResponse(activeEditor, range.start, prompt, cancellationTokenSource);
		commands.executeCommand('setContext', 'wolverine.operationRunning', false);
		await activeEditor.document.save();
	});

	const cancelOpDisposable = commands.registerCommand('wolverine.cancelOperation', () => {
		commands.executeCommand('setContext', 'wolverine.operationRunning', false);
		if (cancellationTokenSource) {
			cancellationTokenSource.cancel();
			cancellationTokenSource = undefined;
		}
	});
	// Add the disposable to the context subscriptions
	context.subscriptions.push(directedHealDisposable, cancelOpDisposable);
}

export function deactivate() { }

function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}
