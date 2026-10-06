Follow AGENTS.md.

You are to develop a small containerized web app. This web app is intended to visualize the quantum confined Stark effect, which demonstrates how the energy levels of electrons in a quantum well shift when a uniform electric field is applied.

The topmost section of the web app should contain a description of the quantum confined Stark effect (QCSE), explained in a way that should be understandable to someone who has completed an undergraduate education in engineering but may not necessarily be familiar with physics, especially quantum physics. A brief segment should describe why the QCSE is relevant for modern technologies, including its influence in LEDs and in electro-optical modulators.

In the section below, the web app should then contain a diagram that dynamically updates according to input parameters. What should be modeled is the potential energy landscape 1D finite quantum well, where the default state is a potential height of V_0 on either side, a tunable well width L, and the first two wavefunctions (the ground energy wavefunction and the first excited state) should be visualized, superimposed on top of the visualization of the 1D quantum well. To be clear, three items should be graphed: the potential energy landscape (which in the default state is a step from finite to zero and then back to finite potential) and two wavefunctions. Ensure the length scale for the quantum well is in nanometers, and ensure that the energy scale for the y-axis of this visualization is on the order of 1 electron volt (1 eV). Sliders should be present at the side to allow the user to tune the V_0 and L parameters. A third slider should additionally include the option to change the electric field, which will start at zero as a default state. Upon changing the electric field, the visualization should update to show 1) how the potential energy landscape changes, sloping as a result of the electric field, and 2) how the wavefunction of the electron changes in response to the electric field.

The Wikipedia page for QCSE will serve as a good starting point: https://en.wikipedia.org/wiki/Quantum-confined_Stark_effect

Use the equations provided on that Wikipedia page, as well as any relevant sources that Wikipedia cites or are otherwise relevant to QCSE, as you will need to numerically calculate electron wavefunctions for two energy states. You will need at least a second order correction from perturbation terms.

This is a Dockerized, containerized project. Inside of the folder you will find docker-demo-example, which contains an extremely basic but functional web app. Follow its general structure.

## Rules
- Run code and tests through `make`, not directly on the laptop.
- Keep changes small; update/add a test for each change.
- Do not edit the Dockerfile unless asked.