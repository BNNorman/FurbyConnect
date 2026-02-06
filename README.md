# FurbyConnect

Python code to demonstrate how to send commands to a Furby.

Thanks to the Sterling work here https://github.com/Jeija/bluefluff I have managed to write a Python program which sends messages to a Furby or Furbies.

Note. This code works on a RPI5 and Win 11- initial work was done using Windows 11 because my Geekom A9 Max box includes a BlueTooth adapter builtin.

You may also be interested in this:- https://github.com/CrazyRobMiles/FurbyESP32/tree/master/M5StickCWeatherFurby

## FurbyConnect.py

This is the main program. It loops, scanning for furbies and then sending commands to them.

With the debug variable set to True it repeats the message "let's give little guy a hand" this gives a warm feeling the code is working. If you set debug=False the code will randomly select one of the messages which are documented in the bluefluff repository.

The code also cycles through the list of antenna colours (Currently Red, Green and Blue). Note the Furby does tend to reset the colour quite quickly.

Also, the Furby mood is set to 'excited'. The mood value could be cycled. I have not noticed any change in behaviour with my code but then it might just control the random messages a Furby normally uses.

## FurbyCommands.py

I have converted the bluefluff actionlist.md into a huge python list in FurbyCommands.py, as best I can.

## FurbyMoods.py

Simple classes to select a mood type and action (set/increment)

## FurbyNotes
Just a program to play the notes Doh,Ray,Me...

## FurbyEyes.py

Just plays the messages with obious eye animations

# issues

If you start 2 Furbies at the same time they will connect to each other and so bluetooth scanning doesn't find them (because they can only communicate with one other Furby at any one time??). I don't think a third Furby joins in normally (Mine didn't). So, start one at a time wait till this program finds them. Detection messages are printed on screen, as are the messages sent to each Furby.

The Furbies can take quite some time to be discovered - though the latest update speeds that up.

# Todo

Research the uploading of own audio and eye animations - people , on github,claim to have done this already.
