# Nintendo-Switch-shiny-hunt
Python script using Computer Vision to hunt for shiny Pokémon on Brilliant Diamond and ,Shining Pearl with other games coming soon

The script uses NXBT from Brikwerk to emulate a switch controller. In the case a pro controller: https://github.com/Brikwerk/nxbt/tree/master

Once the bluetooth connection is made, a confirmation message will display, and then it'll look for a video input.

This project is using a raspberry pi 5 16GB with a CS2 to HDMI in connector from GeekWorm C790. I have not had much luck with it, I was only able to get mine to work by using someone else's script. In doing so, the Red and Blue are swapped making screenshots look off.

After the video input is confirmed, and the controller is connected, it'll read the home screen, confirm it is Brilliant Diamond.
Once confirmed, it'll launch the game using a Macro.

Once in, it takes a screenshot. Currently it is only look for "Still Encounters". What that means is you are standing in front of a legendary. 

It'll use this image to do the encounter, and the game resetting. Currently only works with still encounters. The images after each reset have to be a 90% match (Allows for some models to move slightly)

Afterwards, it'll take a step worked, and press "A" twice to start the encounter. 

There's a delay for any animations to play.

It'll look for the pokemon's name.

If you haven't encountered this pokemon before, a new folder will be created named "Pokemon" and a screen shot of the start of the encounter will be placed in it with the name of that pokemon.

Using that as the base image, the script starts over. It will now treat that image as the "Non-Shiny" form. From then on it compares that image to the one on screen once reaching this point again. 

If it is a 91% match, it restarts. However, if it is lower, that triggers the shiny event where the script stops. 

Each cycle will add an encounter tally to that pokemon in the SHiny folder that was created so you can track how many encounters it took to find it.
