import {
	ExtensionContext,
	workspace,
	Position,
	TextEditor,
	Range,
	commands,
	window
} from 'vscode';
import axios from 'axios';

let openaikey = '';

// See https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events
// Responsiblity of caller to register event listener.
const streamCompletion = async (prompt: string, onDataFunction: (chunk: any) => void): Promise<void> => {
	const messages: any[] = [
		{ role: 'user', content: prompt }
	];
	const headers = {
		['Content-Type']: 'application/json',
		['Authorization']: `Bearer ${openaikey}`,
	};

	const configurationModel =  await workspace.getConfiguration().get('wolverine.model');
	const data = {
		'model': configurationModel || 'gpt-3.5-turbo',
		'messages': messages,
		'temperature': 0.9,
		'stream': true,
	};
	return new Promise(async (resolve) => {
		const response = await axios({
			method: 'post',
			url: 'https://api.openai.com/v1/chat/completions',
			headers: headers,
			data: data,
			responseType: 'stream',
		});
		response.data.on('data', onDataFunction);
		response.data.on('end', () => {
			resolve();
		});
	});
};

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

// Yacine threw most of the complexity into here.
// Holds a buffer in a javascript array, registers a event listener on a server-sent events function, builds the buffer
// Takes a position, and flushes the buffer on a preconfigured cron into the provided cursor position.
const useBufferToUpdateTextContentsWhileStreamingOpenAIResponse = async (activeEditor: TextEditor, position: Position, prompt: string) => {
	let currentCharacter = position.character;
	let currentLine = position.line;
	let buffer: string[] = [];
	let doneStreaming = false;
	const onDataFunction = (word: any) => {
		const newContent = word.toString().split('data: ')
			.map((line: string) => line.trim())
			.filter((line: string) => line.length > 0)
			.map((line: string) => JSON.parse(line).choices[0].delta.content);
		buffer = [...buffer, ...newContent];
	};
	streamCompletion(prompt, onDataFunction).then(() => doneStreaming = true);
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
		// TODO I should make this buffer flush configurable.
		await sleep(30); 
	}
};

const constructPrompt = async (text: string): Promise<string> => {
	const defaultPrompt = `
INSTRUCTIONS: 
The text under 'CODE' has come straight from my text editor. 
When you respond, please only output valid code, and no raw english! If its english, put it under comments.
We want your entire output to be valid codee.
The code sent to you might have some instructions under comments. Follow those instructions.
CODE:
${text}
NEW CODE:
`;
	const configuredPrompt = await workspace.getConfiguration().get('wolverine.prompt');
	if (configuredPrompt) {
		return configuredPrompt + text;
	}
	return defaultPrompt;
};

export async function activate(context: ExtensionContext) {

	let disposable = commands.registerCommand('wolverine.directedHeal', async () => {
		// Forgive me father..
		openaikey = await workspace.getConfiguration().get('wolverine.UNSAFE.OpenaiApiKeySetting') || '';
		const activeEditor = window.activeTextEditor;
		if (!activeEditor) {
			window.showErrorMessage('No text editor is currently active.');
			return;
		}

		const selection = activeEditor.selection;
		let range: Range;
		if (!selection.isEmpty) {
			range = new Range(selection.start, selection.end);
		} else {
			range = activeEditor.document.validateRange(new Range(0, 0, Number.MAX_VALUE, Number.MAX_VALUE));
		}
		const text = activeEditor.document.getText(range);
		const prompt = await constructPrompt(text);
		await deleteRange(activeEditor, range);
		await useBufferToUpdateTextContentsWhileStreamingOpenAIResponse(activeEditor, range.start, prompt);
		await activeEditor.document.save();
	});
	context.subscriptions.push(disposable);
}

export function deactivate() { }

function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}
