# spread

## Introduction
Spread is a small python script that creates a simple model for disease spreading among a population. The idea is to be able to watch the effects of the variation for several key parameters. It takes into account :

- The existing immunity among the population
- The infection probability of the disease
- The contagion time once a person has been infected
- The dead rate
- The quarantaine efficiency : the percentage of the infected people that goes into quarantaine after they have been infected
- The time it takes to put an infected person into quarantaine 

Of course, it is assumed that once a sick person is into quarataine, they cannot infect any other person.

## Output examples

The result is displayed through a simple grid, that shows if an individual is :
- Not ill (white color)
- Immune (grey color)
- Ill (red color)
- In quarantine (yellow color)
- Dead (black color)

At the beginning, a given population is composed of immune people, not immune people, and ill people (the first clusters). 
Right now there a 3 clusters in the application, and that must be changed directly into the python code.

<img src="images/Illustration-1.png" alt="Start Window" width="450" align="middle" />

Once the GO button has been pushed, the simulation goes on, round by round, and one can see how the disease spread.

<img src="images/Illustration-2.png" alt="Modelisation Window" width="450" align="middle" />

## Parameter change

At the end of each simulation, the user that change the parameters as he likes, and test the effect on the spreading of the disease, by pressing the "RESET button", to generate a new "Disease Board", then "GO", to launch the simulation.

## TODO

- Make the number of rounds, the board size and the number of clusters available for change inside the app.
- Make it possible to navigate through the spreading step by step, forward and backward.

## Bugs

Right now there is a bug on Mac OS Mojave that seems to prevent Qt5 from having a nice display behavior. That may result in pressing the "RESET" button having no visual effect. However, the modelisation effectively starts when pressing the "GO" button. This does not happen on Windows.
