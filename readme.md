# DHWInf-Metro

DHWInf-Metro is a metro navigation project designed for Minecraft servers. By entering any starting and ending coordinates or station names, players can easily navigate.

## Features

- Navigate by entering starting and ending coordinates
- Navigate by entering station names
- Fuzzy matching of station names

## Installation

1. Clone this repository locally:
    ```bash
    git clone https://github.com/Logic-Accepted/DHWInf-Metro.git
    ```
2. Navigate to the project directory:
    ```bash
    cd DHWInf-Metro
    ```
3. Install dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

- Update metro station data:
    ```bash
    python ./cli.py --update
    ```
    Normally It is no need to update before use, program will try to get metro data info when it runing first time.
- List all metro stations:
    ```bash
    python ./cli.py --liststation
    ```
- Navigate between stations or coordinates:
    ```bash
    python ./cli.py --metro <station1> <station2>
    python ./cli.py --metro <x1> <z1> <x2> <z2>
    python ./cli.py --metro <x> <z> <station>
    ```
    You can also try typing in station names with similar pronunciations or glyphs, and the program will automatically fuzzy match them.

## Contributing

Issues and requests are welcome, as is code contribution. Please fork this repository and submit a pull request.

## License

This project is licensed under the MIT License. For details, please refer to the LICENSE file.
