const subtractNumbers = (a, b) => {
  return a - b;
};

const multiplyNumbers = (a, b) => {
  return a * b;
};

const divideNumbers = (a, b) => {
  return a / b;
};

function calculate(operation, num1, num2) {
  let result = '';
  if (operation == 'add') {
    result = addNumbers(num1, num2);
  } else if (operation == 'subtract') {
    result = subtractNumbers(num1, num2);
  } else if (operation == 'multiply') {
    result = multiplyNumbers(num1, num2);
  } else if (operation == 'divide') {
    result = divideNumbers(num1, num2);
  } else {
    console.log('Invalid operation');
  }

  return res;
}

const [, , operation, num1, num2] = process.argv;
calculate(operation, num1, num2);
