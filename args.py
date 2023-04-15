import argparse

parser = argparse.ArgumentParser(
  description='Give your python scripts regenerative healing abilities!'
)
parser.add_argument('-y', '--yes', help='Run Every Change made by GPT',
 required=False, action='store_true'
)
parser.add_argument('-f', '--file', help='Path to buggy file', required=True)
parser.add_argument('-m', '--model', help='Model Name', required=False, 
  default='gpt-4'
)
parser.add_argument('-r', '--revert', help='Revert changes from backup file', 
  required=False, default=False
)
parser.add_argument('args', nargs='+', help='Arguments to pass to script')
