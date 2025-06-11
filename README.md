# SE2-IMGtoGame

SE2 Image to schematics to help using regular images or sketches to make a kinda of schematic to manual build in SE2.
Supports English and Portuguese, dark and light mode.

The usage is very simple, all you need it a top view image or sketch and you need a size (Z) in meters the program will try maintaining the ratio between Z and Y but you can optionally add the (Y) in meters.
As long there is a clear difference between the object and the background the program will work. (see the test file)

Basic code that was refined using AI (Chatgpt o3-mini-high); 

Just a hobby :P


## Requirements

    Python 3 (3.13.2) 
    Tkinter Pillow (pip install pillow) 
    NumPy (pip install numpy)
    Top down view image or sketch to be converted and size length in meters (Z) and optional width (Y)   
## Screenshots

![App Screenshot](https://github.com/lds1998/SE2--Hobby/blob/main/Screenshots/Main.png?raw=true)


## Uso/Examples

![Input](https://github.com/lds1998/SE2--Hobby/blob/main/Screenshots/test.jpg?raw=true)
![Image to schematic conversion](https://github.com/lds1998/SE2--Hobby/blob/main/Screenshots/Example01.png?raw=true)
![Output](https://github.com/lds1998/SE2--Hobby/blob/main/Screenshots/Output.png?raw=true)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
