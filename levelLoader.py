
FORMAT_NUM = 0
VERSION = 0

class Level:
    """Level object

    Parse a level with the following format:

        0: magic: "lvlLdr"
        1: magic: "SECTOR:META"
        2: <total number of objects>:<format_number>:<game_version>
        3: <level_name>:<level_description>
        4: magic: "SECTOR:DATA"
        5: <platform_x>:<platform_y>:<platform_width>:<platform_height>:<platform_attributes>
        ...
        6: magic: "EOF"
    """
    def __init__(self,filePath:str):
        self.filePath = filePath
        with open(filePath) as f:
            self.src = f.readlines()

    def load_level(self):
        self.meta = {}
        self.objects = []

        line = ''
        sector = ''

        # Check file magic
        if self.src[0] != 'lvlLdr':
            raise ValueError('Invalid format: Invalid format magic.')

        for line in self.src:
            if line == 'lvlLdr':
                continue

            elif line.startswith('SECTOR'):
                sector = line.split(':')[1]

            elif not sector:
                raise ValueError('Invalid format: Sector not specified.')

            elif sector == 'META':
                if line.count(':') == 3:
                    self.meta['object_count'], self.meta['format'], self.meta['version'] = line.split(':')
                    if int(self.meta['format']) < FORMAT_NUM:
                        raise ValueError(f'Old level format: {self.meta["format"]} (Current is {FORMAT_NUM})')

                    elif int(self.meta['format']) > FORMAT_NUM:
                        raise ValueError(f'Newer level format: {self.meta["format"]} (Current is {FORMAT_NUM})')

                elif line.count(':') == 2:
                    self.meta['name'], self.meta['description'] = line.split(':')

                else:
                    raise ValueError(f'Invalid format: Invalid meta data. (Expected 2-3 fields, got {line.count(':')})')

            elif sector == 'DATA':
                self.objects.append(line.split(':'))


        # Handle EOF
        if self.src[-1].strip() != 'EOF':
            raise ValueError("Invalid format: EOF not found")

    def save_level(self, meta, objects):
        with open(self.filePath, 'w') as file:
            # Write magic strings
            file.write("lvlLdr\n")
            file.write("SECTOR:META\n")
            file.write(f"{len(objects)}:{FORMAT_NUM}:{VERSION}\n")
            file.write(f"{meta['name']}:{meta['description']}\n")
            file.write("SECTOR:DATA\n")

            # Write objects
            for object in objects:
                file.write(":".join(object)+'\n')

            # Write EOF
            file.write("EOF\n")






