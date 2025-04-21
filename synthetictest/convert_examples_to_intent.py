import yaml
import csv

def convert_examples_to_intent():
    with open('../Chatbot/data/nlu.yml', 'r') as file:
        data = yaml.safe_load(file)
        
    intentList = []
    
    for item in data.get('nlu', []):
        if 'intent' in item and 'examples' in item:
            intent_name = item['intent']
            if intent_name == 'greet' or intent_name == 'bot_challenge' or intent_name == 'choose_number':
                continue
            examples = []
            if isinstance(item['examples'], str):
                examples_text = item['examples'].strip()
                if examples_text.startswith('|'):
                    examples_text = examples_text[1:].strip()
                example_lines = examples_text.split('\n')
                for line in example_lines:
                    line = line.strip()
                    if line.startswith('- '):
                        examples.append(line[2:])
                    elif line and not line.startswith('  '):
                        examples.append(line)
            
            intentList.append([intent_name, examples])
    
    return intentList
                    
def write_to_csv(intentList):
  # Group rows by intent
  intent_groups = []
  current_file_rows = []
  file_index = 0
  
  for intent in intentList:
    intent_name = intent[0]
    examples = intent[1]
    
    # Create rows for this intent
    intent_rows = [[intent_name, example] for example in examples]
    
    # If adding this intent would exceed the limit, save current file and start a new one
    if current_file_rows and len(current_file_rows) + len(intent_rows) > 1750:
      # Write current file
      file_path = f'./intent_examples/intent_examples{file_index}.txt'
      with open(file_path, 'w') as file:
        writer = csv.writer(file)
        for row in current_file_rows:
          writer.writerow(row)
      
      # Start a new file
      file_index += 1
      current_file_rows = intent_rows
    else:
      # Add to current file
      current_file_rows.extend(intent_rows)
  
  # Write the last file if there's anything left
  if current_file_rows:
    file_path = f'./intent_examples/intent_examples{file_index}.txt'
    with open(file_path, 'w') as file:
      writer = csv.writer(file)
      for row in current_file_rows:
        writer.writerow(row)
  
if __name__ == "__main__":
    intentList = convert_examples_to_intent()
    write_to_csv(intentList)
  
