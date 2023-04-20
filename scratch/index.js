const countCharacters = (text) => text.replace(/\n/g, '').length;
const countNewLines = (text) => text.match(/\n/g)?.length || 0;
const countTextStream = (textStream) => {
  const numberOfCharacters = countCharacters(textStream);
  const numberofNewLines = countNewLines(textStream);
  return { numberOfCharacters, numberofNewLines };
};

const main = () => {
  const textStream = "A B C D E F G H I J K L M N O P Q \n\n R S T U V";
  const result = countTextStream(textStream);
  console.log(result);
};

main();