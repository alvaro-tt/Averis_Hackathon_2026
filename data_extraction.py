import json

# extract from json file and converts into native python data structure (like dictionary or list)
def convert_to_list(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data

def extract_field(text, label):
    for line in text.split(", "):
        if label.lower() in line.lower():
            return line.split(":", 1)[1].strip()
    return None


if __name__ == '__main__':
    text_file = convert_to_list('sample.json')
    print(extract_field(text_file, 'shipper'))