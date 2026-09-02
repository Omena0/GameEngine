import os

FORMAT_NUM = 2

class Level:
    """Level object

    Parse a level with the following format:

        0: magic: "lvlLdr"
        1: magic: "SECTOR:META"
        2: <total number of objects>:<format_number>:<game_version>
        3: <level_name>:<level_description>
        4: magic: "SECTOR:DATA"
        5: <objet_type>:<object_x>:<object_y>:<object_width>:<object_height>:<object_attributes>:<object_texture>
        ...
        6: magic: "EOF"
    """
    def __init__(self,filePath:str, game_ver:int):
        self.filePath = filePath
        self.game_ver = game_ver
        if os.path.exists(filePath):
            with open(filePath) as f:
                self.src = f.read().splitlines()
        else:
            self.src = ''

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
                if line.count(':') == 2:
                    self.meta['object_count'], self.meta['format'], self.meta['version'] = line.split(':')
                    if int(self.meta['format']) < FORMAT_NUM:
                        raise ValueError(f'Old level format: {self.meta["format"]} (Current is {FORMAT_NUM})')

                    elif int(self.meta['format']) > FORMAT_NUM:
                        raise ValueError(f'Newer level format: {self.meta["format"]} (Current is {FORMAT_NUM})')

                elif line.count(':') == 1:
                    self.meta['name'], self.meta['description'] = line.split(':')

                else:
                    raise ValueError(f'Invalid format: Invalid meta data. (Expected 2-3 fields, got {line.count(':')})')

            elif sector == 'DATA':
                if line == 'EOF':
                    return self.meta, self.objects
                self.objects.append(line.split(':'))

        raise ValueError("Invalid format: EOF not found")

    def save_level(self, meta, objects):  # sourcery skip: extract-method
        with open(self.filePath, 'w') as file:
            # Write magic strings
            file.write("lvlLdr\n")
            file.write("SECTOR:META\n")
            file.write(f"{len(objects)}:{FORMAT_NUM}:{self.game_ver}\n")
            file.write(f"{meta['name']}:{meta['description']}\n")
            file.write("SECTOR:DATA\n")

            # Write objects
            for sprite in objects:
                object = sprite.object
                attr = ''.join(f'{key}={str(value).replace(',','~')},' for key, value in object.attributes.items()).removesuffix(',').replace(', ',',').replace('~ ','~')

                file.write(f'{object.type}:')
                file.write(f'{int(sprite.x)}:')
                file.write(f'{int(sprite.y)}:')
                file.write(f'{int(object.width)}:')
                file.write(f'{int(object.height)}:')
                file.write(f'{attr}')
                if object.sprite.texture[0]:
                    file.write(f':{object.sprite.texture}'.replace(', ',','))
                file.write('\n')

            # Write EOF
            file.write("EOF")






