# Supplementary information

## S1 Appendix. Derivation of the JR Model Equations

The Jansen-Rit and related models are often discussed in terms of a convolution integral for the synaptic impulse response function, as well as the corresponding equivalent second-order differential equation, which is typically what is used in numerical simulations. The mathematical relationship between these is however rarely given in literature sources, and so we provide that here, with a full derivation of the JR differential equation from its impulse response, using the Laplace transform as it simplifies convolution operations by turning them into algebraic manipulations in the Laplace domain.

The synaptic impulse response is defined as an alpha function, which is described by the following equations:

[Formula on PDF page 1 (14)](../assets/supp_figs/s1-formula-p0001-013.jpg)

with _α_ as the maximum amplitude of the PSP and _β_ the rate constant parameter. The first step consists of finding the Laplace transform of _h_ ( _t_ ), denoted as _H_ ( _s_ ), which is defined as follows:

[Formula on PDF page 1 (19)](../assets/supp_figs/s1-formula-p0001-018.jpg)

Now, with an expression for _H_ ( _s_ ) in the Laplace domain, and given that _y_ ( _t_ ) is equal to the convolution of _h_ ( _t_ ) and _x_ ( _t_ ), we can represent this relationship in the Laplace domain as:

[Formula on PDF page 2 (3)](../assets/supp_figs/s1-formula-p0002-002.jpg)

[Formula on PDF page 2 (4)](../assets/supp_figs/s1-formula-p0002-003.jpg)

[Equation (14)](../assets/supp_figs/s1-formula-p0002-004.jpg)

[Equation (15)](../assets/supp_figs/s1-formula-p0002-005.jpg)

[Formula on PDF page 2 (9)](../assets/supp_figs/s1-formula-p0002-008.jpg)

Since _s_<sup>2</sup> _Y_ ( _s_ ) corresponds to the second derivative in the time domain, translating equation (40) back into the time domain, we obtain:

[Formula on PDF page 2 (13)](../assets/supp_figs/s1-formula-p0002-012.jpg)

This corresponds to the commonly used JR second-order differential equation, which can be rewritten in the form of two first-order ODE’s:

[Formula on PDF page 2 (17)](../assets/supp_figs/s1-formula-p0002-016.jpg)

[Formula on PDF page 2 (18)](../assets/supp_figs/s1-formula-p0002-017.jpg)

with _y_ ( _t_ ) representing the average postsynaptic membrane potential (output of the PSP block).

## S2 Appendix. Transfer Function of the Models

In addition to comparing the numerical simulation outputs, we also simulated the analytical (or linearized) power spectra of the models. These analytical models are used for stability analysis, offering clear insights into how a system responds to changes in inputs. Moreover, they provide explicit solutions, enhancing our understanding of the system’s behavior. The transfer functions for both the JR and MDF models are derived from graph control analysis. The equations for the LW model are sourced from Hartoyo et al. (2019) [1], while those for the RRW model are from Robinson et al. (2002) [2].

[Figure on PDF page 1 (11)](../assets/supp_figs/s2-figure-p0001-010.jpg)

**Fig A.** **_Transfer function of each of the four studied models (JR, MDF, LW, and RRW) with the corresponding analytical power spectra_** The transfer function of JR and MDF were derived using graph control analysis. The derivations for LW transfer function are sourced from [1], and for RRW from [2]

[Figure on PDF page 2 (2)](../assets/supp_figs/s2-figure-p0002-001.jpg)

**Fig B.** **_Analytical power spectra of the four models together._** After linearization, the models continue to generate alpha rhythms with a peak between 8-12 Hz (represented by the red zone). Among the models, RRW is unique in capturing the harmonics at higher frequencies in its linearized form. JR exhibits a broader peak compared to the others, while LW has a lower peak height.

### References

[1] Hartoyo A, Cadusch PJ, Liley DT, Hicks DG. Parameter estimation and identifiability in a neural population model for electro-cortical activity. PLoS computational biology. 2019;15(5):e1006694.

[2] Robinson P, Rennie C, Rowe D. Dynamics of large-scale brain activity in normal arousal states and epileptic seizures. Physical Review E. 2002;65(4):041924.

## S3 Appendix. Derivation of Stability Analysis for JR and LW

For JR, similar to Grimbert et al. (2006) [1], the fixed points are determined by setting the derivatives to 0. With some manipulations, the equilibrium points in the ( _C, y_ 1 _− y_ 2) plane with _y_ = _y_ 1 _− y_ 2 are equal to:

[Equation (1)](../assets/supp_figs/s3-formula-p0001-007.jpg)

The stability of the fixed points is then defined using the Jacobian matrix

[Jacobian matrix Y (equilibrium stability)](../assets/supp_figs/s3-formula-p0001-010.jpg)

with _y_ corresponding to the fixed point of interest and _y_ 0( _y_ ) = ( _A_ / _a_ ) _S_ ( _y_ ). Stability is then defined by calculating the eigenvalues of the matrix **Y** for each fixed point, and looking at the sign of the real part of the eigenvalues. The system is stable if all the eigenvalues have a negative real part. If at least one of the eigenvalues has a positive real part, it is considered as an unstable fixed point.

Using a similar method (estimation of the fixed point, following an assessment of the stability of the fixed points by looking at the real part of the eigenvalues of the Jacobian matrix), the LW equilibrium points’ stability was also determined. The full calculation and equations are detailed in the appendix of Hartoyo et al. (2019) [2] and also in S9 Appendix. Briefly:

The equilibrium point equations can be reduced to:

[Equations (2)-(3)](../assets/supp_figs/s3-formula-p0001-025.jpg)

with

[Equations (4)-(7)](../assets/supp_figs/s3-formula-p0001-028.jpg)

The fixed points for _Ve_ and _Vi_ are then estimated by finding the values for which values these two equations intersect.

The Jacobian matrix is:

[Jacobian matrix F_i,j (symbolic and evaluated forms)](../assets/supp_figs/s3-formula-p0002-005.jpg)

with

[Equations (8)-(9)](../assets/supp_figs/s3-formula-p0002-008.jpg)

We then replace _Ve_ and _Vi_ with the equilibrium points computed previously, and the real parts of the eigenvalues of this Jacobian matrix are then examined to assess their stability.

### References

[1] Grimbert F, Faugeras O. Bifurcation analysis of Jansen’s neural mass model. Neural computation. 2006;18(12):3052–3068

[2] Hartoyo A, Cadusch PJ, Liley DT, Hicks DG. Parameter estimation and identifiability in a neural population model for electro-cortical activity. PLoS computational biology. 2019;15(5):e1006694.

## S4 Appendix. Stability Analysis Low Noise JR and LW of Connectivity E-I parameters

In the main text, we presented the stability analysis of the E-I connectivity parameters with standard input. Our aim was to demonstrate the changes in this analysis when low noise input is introduced, highlighting the differences between the JR and LW models. Specifically, we showed that in the JR model, a Hopf bifurcation occurs at the alpha rhythm. In contrast, the alpha rhythm generated with LW model is noise-driven, as without noise, it behaves as a damped oscillator and reaches a fixed point instead of oscillating.

[Fig A](../assets/supp_figs/s4-figure-p0001-010.jpg)

**Fig A.** **_Fixed points and corresponding phase planes of JR and LW at specific connectivity values with low noise input_** For the JR model, **A1** and **A2** correspond to the fixed points of JR with low noise, and the corresponding phase planes for specific connectivity values. Similarly to JR, the fixed points of LW are presented with low noise and the corresponding phase plane for specific connetivity values in **B1** and **B2** . Unstable fixed points are red, whereas stable fixed points are blue. The cross phase plan in JR correspond to the standard alpha rhythm parameters, whereas the star phase plane in LW correspond to the standard alpha parameters.

## S5 Appendix. Phase plane of JR in 3D

For the stability analyses in Fig. 11, we have only presented the phase plane with the pyramidal and inhibitory population output voltages. Considering the trajectory of the third excitatory neural population activity can provide a better understanding of the full picture, as presented in Fig. A.

[Figure on PDF page 1 (13)](../assets/supp_figs/s5-figure-p0001-012.jpg)

**Fig A.** **_Phase plane of JR for different E-I connectivity parameters._** The trajectory of the three neural populations (with _y_ 0, _y_ 1, and _y_ 2 corresponding to the output of the PSP block for the pyramidal cells, excitatory interneurons, and inhibitory interneurons, respectively) can be inferred by examining the stability of their respective fixed point (red). When _C_ 3 _,_ 4 = 27, the fixed point is stable and no oscillations occur. For _C_ 3 _,_ 4 = 33.5, the system enters a limit cycle with the oscillation frequency of alpha. Finally, when _C_ 3 _,_ 4 = 40.5, the limit cycle widens and the frequency of oscillation is reduced.

As seen in our previous phase plane analysis, for specific connectivity parameters, the system either reaches a fixed point or enters a limit cycle defining the frequency of oscillation. The results closely resemble those in Fig. 11, implying that the dynamics primarily involve interactions between the pyramidal and inhibitory populations, with minimal contribution from the third population in this case.

## S6 Appendix. Comparison of MDF and JR connectivity parameter spaces

By setting the parameters to be the same between JR and MDF, we compare the connectivity parameter space of the two models (Fig. A).

[Fig A](../assets/supp_figs/s6-figure-p0001-015.jpg)

**Fig A.** **_Connection strength parameter spaces for JR and MDF with similar parameter settings._** In the top, for MDF _γ_ 5 = 16, and at the bottom _γ_ 5 = 0. The general shape of the dynamics is very similar between the two, suggesting that the effects of connectivity are the same. However, MDF tends to generate oscillations of higher frequencies for identical connectivity parameter sets, even when the _γ_ 5 connection is removed.

In the top row of Fig. A, we compare JR against MDF with the self-inhibitory connection. We observe a similar triangular boundary shape within which the system oscillates. However, MDF tends oscillate at higher frequency that exceed the alpha range (Fig. A, MDF top row, colors are brighter than JR). When the self-inhibitory connection is removed in MDF (Fig. A, MDF bottom row), the system now oscillates at the alpha frequency. It does not present lower frequencies, such as those in the JR model where we have slower oscillations. Thus, MDF seems to oscillate at higher frequencies than JR. Nonetheless, we observe that the two models share this similar triangular shape with non-oscillatory behavior when _C_ 3 and _C_ 4 are too low, suggesting similar global dynamics. The main conclusion drawn from this analysis is that the self-inhibitory connection introduced in MDF grants the model the ability to generate oscillations at a higher frequency than alpha, a more challenging capability compared to JR.

## S7 Appendix. 4D JR connectivity analysis

In the JR model, our focus was specifically on _C_ 3 ( _P → I_ ) and _C_ 4 ( _I → P_ ) as the E-I loop, but there is also the interaction between excitatory interneurons and pyramidal cells ( _C_ 1 ( _P → E_ ) and _C_ 2 ( _E → P_ )) to consider. Typically, the ratio between these values is varied. By simulating time series for different values of _C_ with the standard ratio values ( _C_ 1 = _C_ , _C_ 2 = 0.8 _∗ C_ , _C_ 3 = 0.25 _∗ C_ and _C_ 4 = 0.25 _∗ C_ ), we can infer that increasing values of C lead to a decrease in the frequency of oscillation up to a certain point (Fig. A), which concurs with results from Jansen and Rit (1995) [1].

[Fig A](../assets/supp_figs/s7-figure-p0001-010.jpg)

**Fig A.** **_Simulated time series of JR for different connectivity C values._** From top to bottom: _C_ = 68, _C_ = 128, _C_ = 135, _C_ = 270, _C_ = 675, _C_ = 1350. As connectivity values increase, the frequency of oscillations decreases up to _C_ = 675.

Changes in the frequency of oscillation as a function of connectivity ratios are presented in the form of 4D heatmaps in a 2D space (Fig. B). The general trend observed is that higher connectivity values result in slower oscillations, as expected.

[Fig B](../assets/supp_figs/s7-figure-p0001-014.jpg)

**Fig B.** **_Variation in the frequency of oscillation as a function of connection strength for JR for different_** _C_ **_values._** From left to right: _C_ = 68, _C_ = 128, _C_ = 135 and _C_ = 270. The outer axes _C_ 1 _− C_ 2 represent the excitatory loop, while the inner axes _C_ 3 _− C_ 4 represent the inhibitory loop. The results correlate with what is observed in the time series. The parameter space is obtained by changing the ratio of each connection (i.e: _C_ 1 = 0.8 corresponds to _C_ 1 = 0.8 _∗ C_ )

To observe the different trends that emerge, we focused on the case where _C_ equals 135 and investigated the different possible combinations of parameters on the outer and inner axes (Fig. C).

[Figure on PDF page 2 (1)](../assets/supp_figs/s7-figure-p0002-000.jpg)

**Fig C.** **_Connection strength parameter spaces for Jansen-Rit in different combinations with C=135._** Each combination reveals a distinct pattern, aiding in visualizing the relationships among all the connectivity parameters. From left to tight: 1) Outer axes _C_ 1 _− C_ 2 Inner axes _C_ 3 _− C_ 4; 2) Outer axes _C_ 1 _− C_ 3; Inner axes _C_ 2 _− C_ 4; 3) Outer axes _C_ 2 _− C_ 3; Inner axes _C_ 1 _− C_ 3; 4) Outer axes _C_ 3 _− C_ 4; Inner axes _C_ 1 _− C_ 2

Clear patterns emerge in two different cases. When _C_ 3 ( _P → I_ ) and _C_ 4 ( _I → P_ ) are on the outer axes, a continuous change in the frequency of oscillation is observed. Similarly, when comparing _C_ 1 ( _P → E_ ) against _C_ 3 ( _P → I_ ), a concrete pattern is evident, with more pronounced changes in the frequency of oscillation when _C_ 3 is altered. These results reinforce the idea that the main loop influencing the frequency of oscillation is the interaction between the pyramidal and inhibitory populations, raising the question of whether adding an additional excitatory population is truly necessary, even though it would be more biologically realistic.

[Figure on PDF page 2 (8)](../assets/supp_figs/s7-figure-p0002-007.jpg)

**Fig D.** **_Connection strength parameter space for_** _C_ 2 **_(_** _E → P_ **_) and_** _C_ 4 **_(_** _I → P_ **_) in JR._** Higher values of _C_ 4 lead to a decrease in rhythmic oscillations. The highest frequency of oscillation occurs when _C_ 4 is at a ratio of 0.25, and _C_ 2 is around 1.0. If _C_ 4 is too low, a very noisy signal is generated.

### References

- [1] Jansen BH, Rit VG. Electroencephalogram and visual evoked potential generation in a mathematical model of coupled cortical columns. Biological cybernetics. 1995;73(4):357–366.

## S8 Appendix. 3D parameter space with MDF

We simplified the 5-dimensional connection parameter space into a 3-dimensional representation for the MDF model, using its linearized version. Stability is assessed by looking at the system’s poles within the transfer function of the system. The aim was to establish a parallel with the 3D ‘xyz’ corticocortical/corticothalamic/intrathalamic lumped gains reduced parameter space discussed in a number of studies using the RRW model (although for reasons of space we have not focused on that aspect of RRW in the present paper [1–5]), and determine the effects of the loops on the dynamics of the MDF model.

[Figure on PDF page 1 (11)](../assets/supp_figs/s8-figure-p0001-010.jpg)

[Figure on PDF page 1 (12)](../assets/supp_figs/s8-figure-p0001-011.jpg)

**Fig A.** **_Visualization of dynamical regimes of the MDF model in a 3D setting using the linearized expression._** The x-axis corresponds to effect of the excitatory loop ( _γ_ 1 _∗ γ_ 2); the y-axis represents the effect of the inhibitory loop ( _γ_ 3 _∗ γ_ 4); and the z-axis is the effect of the self-inhibitory loop ( _γ_ 5). As _γ_ 5 values increase, the system tends to oscillate at a higher frequency.

The aim here is to easily visualize the regions of stability and dynamics as a function of the ‘loops’, rather than a single connectivity parameter. As expected, with the increase in the self-inhibitory connection (z-axis), the dominant frequency of oscillation gradually shifts from theta to alpha and then to the beta range.

### References

- [1] Robinson P, Rennie C, Rowe D. Dynamics of large-scale brain activity in normal arousal states and epileptic seizures. Physical Review E. 2002;65(4):041924.

- [2] Robinson PA, Rennie C, Rowe DL, O’Connor S, Gordon, E. Multiscale brain modelling. Philosophical Transactions of the Royal Society B: Biological Sciences. 2005;360(1457):1043–1050.

- [3] Roberts J, Robinson P. Corticothalamic dynamics: structure of parameter space, spectra, instabilities, and reduced model. Physical Review E. 2012;85(1):011910.

- [4] Breakspear M, Roberts JA, Terry JR, Rodrigues S, Mahant N, Robinson PA. A unifying explanation of primary generalized seizures through nonlinear brain modeling and bifurcation analysis. Cerebral Cortex. 2006;16(9):1296–1313.

- [5] Abeysuriya R, Rennie C, Robinson P. Physiologically based arousal state estimation and dynamics. Journal of Neuroscience Methods. 2015;253:55–69.

## S9 Appendix. Full Model Equations

Partial and diagrammatic presentations of the differential equations for each of the four models are given in Figs 4-7. In this Appendix, we provide the complete differential equations for each model, as well as tables describing the model parameters and state variables.

### Jansen-Rit model equations

The differential equations for the JR model are

[Formula on PDF page 1 (14)](../assets/supp_figs/s9-formula-p0001-013.jpg)

[Formula on PDF page 1 (15)](../assets/supp_figs/s9-formula-p0001-014.jpg)

[Formula on PDF page 1 (16)](../assets/supp_figs/s9-formula-p0001-015.jpg)

[Formula on PDF page 1 (17)](../assets/supp_figs/s9-formula-p0001-016.jpg)

[Formula on PDF page 1 (18)](../assets/supp_figs/s9-formula-p0001-017.jpg)

[Formula on PDF page 1 (19)](../assets/supp_figs/s9-formula-p0001-018.jpg)

Here and in the rest of this paper we have maintained the same notation as in Jansen and Rit [1] where y0, y1, and y2 correspond to the outputs of the pyramidal, excitatory, and inhibitory PSP block, respectively. p(t) represents the external input applied to the system, usually noise. A and B define the maximum amplitude of excitatory and inhibitory PSP, respectively. a and b represent the collective effect of the inverse of the time constant of the passive membrane and the entirety of the spatially dispersed delays within the dendritic network for the excitatory and inhibitory populations, respectively. C1 to C4 are the connectivity constants.

For the connectivity parameters, we wanted to mention that C1 and C3 slightly differ from C2 and C4 in the mathematical expression. The JR model assumes equal synaptic input from the pyramidal cell population to the other two populations, setting these constants to 1. In contrast, the synaptic coefficients at the excitatory and inhibitory dendrites are varied (corresponding to C1 (P → E) and C3 (P → I)). Conversely, for pyramidal cells, the synaptic coefficients at their dendrites remain fixed (1 and -1 for excitatory and inhibitory interneurons, respectively), and excitatory and inhibitory neurons synapse onto pyramidal cells differently (represented by C2 (E → P ) and C4 (I → P ). Therefore, C1 and C3 function as synaptic coefficients, while C2 and C4 serve as connectivity constants, as illustrated in the detailed schematic. Mathematically, this means that C1 and C3 are applied within the nonlinear function, while C2 and C4 are applied outside. However, in practical terms, all these parameters are described as connectivity parameters and can be considered analogous and interrelated. Furthermore, all the values are scaled by a global connectivity parameter. See Cook et al. 2021 [2] for a further explanation of this nuanced aspect of the JR model system.

[Table A. JR parameters](../assets/supp_table/s9-table-a.csv)

| Symbol | Description | Value |
| --- | --- | --- |
| e0 | Firing rate at threshold | 2.5 s^(−1) |
| V0 | Firing threshold | 6 mV |
| r | Slope reflecting the variance of firing thresholds within<br>the population | 0.56 mV^(−1) |
| A | Maximum amplitude of excitatory PSP (EPSP) | 3.25 mV |
| B | Maximum amplitude of inhibitory PSP (IPSP) | 22 mV |
| a and b | Lumped representation of the sum of the reciprocal of<br>the time constant of passive membrane and all other<br>spatially distributed delays in the dendritic network | a = 100 s^(−1)<br>b = 50 s^(−1) |
| C1 | Connectivity constant:<br>Represents the number of<br>synapses made by the feed forward neurons to the dendrites of the excitatory feedback loop | C = C1<br>135 |
| C2 | Connectivity constant: Proportional to the number of<br>synapses made by the excitatory feedback loop to the<br>dendrites of the feedforward neurons | C2 = 0.8C |
| C3 | Connectivity constant: number of synapses made by the<br>feedforward neurons to the dendrites of the inhibitory<br>feedback loop | C3 = 0.25C |
| C4 | Connectivity constant: Proportional to the number of<br>synapses made by the inhibitory feedback loop to the<br>dendrites of the feedforward neurons | C4 = 0.25C |
| P(t) | External pulse density consisting of activity originating<br>from adjacent and more distant cortical columns and<br>from subcortical structures (e.g. thalamus) | Uniform noise (or normal, constant) |

Table A. JR parameters with biological descriptions and corresponding values to generate alpha rhythm

### Moran-David-Friston model equations

The form of the differential equations for the MDF model are

[MDF equation (7)](../assets/supp_figs/s9-appendix-formula-p0002-eq7.jpg)

[MDF equation (8)](../assets/supp_figs/s9-appendix-formula-p0002-eq8.jpg)

[MDF equation (9)](../assets/supp_figs/s9-appendix-formula-p0002-eq9.jpg)

[MDF equation (10)](../assets/supp_figs/s9-appendix-formula-p0002-eq10.jpg)

[MDF equation (11)](../assets/supp_figs/s9-appendix-formula-p0002-eq11.jpg)

[MDF equation (12)](../assets/supp_figs/s9-appendix-formula-p0002-eq12.jpg)

[Formula on PDF page 3 (3)](../assets/supp_figs/s9-formula-p0003-002.jpg)

[Formula on PDF page 3 (4)](../assets/supp_figs/s9-formula-p0003-003.jpg)

[Formula on PDF page 3 (5)](../assets/supp_figs/s9-formula-p0003-004.jpg)

The vi values represent the membrane potential of the subpopulations and ii denoting their current. Specifically, v1 and i1 describe the excitatory interneurons, v2,3,6 and i2,3 the pyramidal cells, and finally v4,5,7 and i4,5 the inhibitory interneurons. The γi values are the connection strengths between the populations. He and κe are the maximum amplitude and the rate constant associated with EPSP, respectively. Similarly, Hi and κi represent the same parameters for the IPSP.

[Table B. MDF parameters](../assets/supp_table/s9-table-b.csv)

| Symbol | Description | Value |
| --- | --- | --- |
| ρ1 | For shape of sigmoid: Can straighten more or less the slope | 2 |
| ρ2 | For position of sigmoid: Can shift the curve right or left | 1 |
| He | Maximum amplitude of excitatory PSP (EPSP) | 10 mV |
| Hi | Maximum amplitude of inhibitory PSP (IPSP) | 22 mV |
| κe and κi | Lumped representation of the sum of the rate constants of passive<br>membrane and other spatially distributed delays in the dendritic<br>tree | κe = 250 s^(−1)<br>κi<br>=<br>62.5<br>s^(−1) |
| γ1 | Coupling strength: Between pyramidal cells and macrocolumn u<br>(in excitatory spiny cells in granular layer) | 128 |
| γ2 | Coupling strength: Between excitatory spiny cells in granular layer<br>and pyramidal cells | 128 |
| γ3 | Coupling strength: Between pyramidal cells (excitatory) and inhibitory interneurons | 64 |
| γ4 | Coupling strength: Between inhibitory interneurons and pyramidal<br>cells | 64 |
| γ5 | Coupling strength: Inhibitory-Inhibitory coupling (recurrent connection) | 1 |

Table B. MDF parameters with biological descriptions and corresponding values to generate alpha rhythm

### Liley-Wright model equations

For the LW model, the differential equations are

[Formula on PDF page 4 (5)](../assets/supp_figs/s9-formula-p0004-004.jpg)

[Formula on PDF page 4 (6)](../assets/supp_figs/s9-formula-p0004-005.jpg)

Nxx are the inter- and intra-connectivities between the two populations. pei and pee are the external inputs. Ixx are the postsynaptic potentials, and Vxx are the soma membrane potentials. Γe,i and γe,i are the peak amplitude and rate constant PSPs for excitatory and inhibitory population, respectively. The model also includes passive membrane time constants represented by τe,i, mean resting membrane potentials Ve,i<sup>r</sup>, and mean equilibrium potentials Ve,i<sup>eq</sup>.

[Table C. LW parameters](../assets/supp_table/s9-table-c.csv)

| Symbol | Description | Value |
| --- | --- | --- |
| S^(max)<br>(e,i) | Excitatory/Inhibitory population mean maximal firing rates | 500, 500 s^(−1) |
| µ(e,i) | Excitatory/Inhibitory population thresholds (spike threshold) | -50, -50 mV |
| σ(e,i) | Standard deviation for spike-threshold in excitatory/inhibitory<br>population | 5, 5 mV |
| Γe | Excitatory postsynaptic potential peak amplitude (at the site of<br>synaptic activation) | 0.71 mV |
| Γi | Inhibitory postsynaptic potential peak amplitude (at the siyte of<br>synaptic activation) | 0.71 mV |
| γ(e,i) | Excitatory/Inhibitory postsynaptic potential rate constant | 300, 65 s^(−1) |
| τ(e,i) | Passive membrane decay time constant | 0.094, 0.042 s |
| V ^(r)<br>(e,i) | Mean resting membrane potential | -70, -70 mV |
| V ^(eq)<br>(e,i) | Mean equilibrium potential associated with excitation or inhibition | 45, -90 mV |
| N ^(β)<br>(ee,ei) | Total number of connections that a cell of type e, i receives from<br>excitatory cells via intra-cortical fibres (Weight connections) | 3000, 3000 |
| N ^(β)<br>(ie,ii) | Total number of connections that a cell of type e,i receives from<br>inhibitory cells via intra-cortical connections (Weight connections) | 500, 500 |
| p(ee,ei) | Excitatory extra-cortical input to excitatory, inhibitory cells | 3.46, 5.07s^(−1) |
| p(ie,ii) | Inhibitory extra-cortical input to excitatory, inhibitory cells | 0, 0 s^(−1) |

Table C. LW parameters with biological descriptions and values to generate alpha rhythm

### Robinson-Rennie-Wright model equations

Finally, the differential equations of the RRW are as follows

[Formula on PDF page 5 (9)](../assets/supp_figs/s9-formula-p0005-008.jpg)

with Ve, Vr, and Vs representing the potential of the cortical population, the reticular nucleus, and the relay nuclei, respectively. νxx denote the connection strengths parameters. α and β refer to the decay and rise time of the impulse response, representing the dendritic rate. t0 is the conduction delay between thalamic and cortical projections. Finally, γe stands for the cortical damping rate, which is exclusively applied to the cortical population. This final differential equation for determining φe is related to the PDE damped wave equation, used to consider spatial variations [3]. However, in the case of spatial uniformity, the wave equation simplifies to an ODE [4].

[Table D. RRW parameters](../assets/supp_table/s9-table-d.csv)

| Symbol | Description | Value |
| --- | --- | --- |
| Qmax | Maximum attainable firing rate of individual neurons | 340 s^(−1) |
| σ^(′)π√3 | Standard deviation of the threshold distribution in the neural population | 3.8∗π√3 ≈<br>5.9 mV |
| θ | Mean firing threshold | 12.92 mV |
| γe | Cortical damping rate (Axonal velocity/Range) | 116 s^(−1) |
| 1/α | Decay time (of impulse response, dendritic rate) | 83.33 s^(−1) |
| 1/β | Rise time (of impulse response, dendritic rate) | 769.23 s^(−1) |
| t0 | Corticothalamic loop delay (Loop distance/Axonal velocity = conduction delay through thalamic nuclei and projections) | 80 ms |
| vee | Neesee: Mean number of synapses X strength of the response to a<br>unit signal | 3.03 mVs |
| −vei | −Neisei | 6.00 mVs |
| ves | Nesses | 2.06 mVs |
| vse | Nsesse | 2.18 mVs |
| −vsr | −Nsrssr | 0.83 mVs |
| vre | Nresre | 0.33 mVs |
| vrs | Nrssrs | 0.03 mVs |
| vsn | Nsnssn | 0.98 mVs |

Table D. RRW parameters with biological descriptions and values to generate alpha rhythm

### References

- [1] Jansen BH, Rit VG. Electroencephalogram and visual evoked potential generation in a mathematical model of coupled cortical columns. Biological cybernetics. 1995;73(4):357–366.

- [2] Cook BJ, Peterson AD, Woldman W, Terry JR. Neural Field Models: historical perspectives and recent advances. arXiv preprint arXiv:210310554. 2021;.

- [3] Robinson PA, Rennie CJ, Wright JJ. Propagation and stability of waves of electrical activity in the cerebral cortex. Physical Review E. 1997;56(1):826.

- [4] Zhao X, Robinson PA. Generalized seizures in a neural field model with bursting dynamics. Journal of computational neuroscience. 2015;39(2):197–216.

## 10 Appendix. Additional background literature

For interested readers, we provide here some further background literature on early history of NPMs and other alpha theories:

### Tracing the roots of NPMs: early history

The notion of neural _masses_ was introduced in various forms during the 1950s and 1960s [1,2], and consolidated in the 1970s primarily through the highly influential work of Freeman, Wilson & Cowan, Amari, and Nunez. It was Freeman who originally used the term ‘neural mass action model’ [3–5], articulating many of the neurobiological and mathematical fundamentals as they are understood today in a wide-reaching monograph on the subject [5]. Here, Freeman also develops the theory of ‘K-sets’ which are based on a hierarchy of interacting sets of neural populations or masses, and used to model neural population dynamics with ordinary differential equations (ODEs) to simulate mesoscopic local field potentials [6]. The levels are designated as K0, KI, KII, and KIII, with the K0 set corresponding to a model characterized by noninteractive collections of neurons with globally common inputs and outputs, KI to pairs of interacting K0 sets, and so on. Freeman’s research on the olfactory bulb and prepyriform cortex of cats and rabbits [5, 7] provides valuable experimental data that has been used to define mathematical formulations and parameter settings in many NMMs, which is further discussed in section 3.2.4. Furthermore, Freeman’s contributions on the use of the sigmoidal operator for mapping membrane potential to firing rate remains a critical component of many NMMs, the validity of which will be elaborated on in section 4.2. Even though Freeman coined the term neural masses and laid much of the groundwork, many of the core mathematical principles of NMMs were first proposed in the work of Wilson & Cowan (WC; [8]), which itself builds upon earlier work by Beurle (1956) [1]. WC’s implementation introduced and solidified an approach to modelling neural dynamics and brain function. This approach consists of analyzing the collective properties of a large number of neurons using methods from statistical mechanics rooted in the mean-field framework [9,10]. By omitting potential spatial arrangement of synaptic connections, their model offers a minimalistic NMM representation that has been leveraged to develop several simple yet biophysically plausible models (eg [11,12]). As shown in Fig. A, the canonical WC model consists of two neural masses with one excitatory and one inhibitory population [8, 12]. Two nonlinear ODEs describe the dynamics of those two synaptically coupled populations in the neocortex [13, 14]. The WC system is thus a coarsegrained description of the overall activity and mesoscale neuronal network structure of a patch of (usually cortical) tissue, as is typical of NPMs. By varying the connectivity strength and the input strength to each population, it is possible to generate a diversity of dynamical behaviors that are characteristic of observed activity in the brain, such as multistability, oscillations, traveling waves, and spatial patterns [11].

A simplified version of the WC equations shown in Fig. A has been previously implemented by Abeysuriya et al. (2018) [15] in a network of neural masses to generate alpha oscillations. These two populations are described as follows:

[Figure on PDF page 2 (5)](../assets/supp_figs/s10-figure-p0002-004.jpg)

**Fig A.** **_Wilson-Cowan model topography and mathematical expression_** . The model aims to represent a cortical column within the brain, consisting of an excitatory and an inhibitory population. These two connected populations each have a self-connection and external activity as input. Dynamics are expressed with nonlinear ordinary differential equations which are shown on the right for each neural population. Nonlinearity is introduced with the sigmoidal operator corresponding to the activation function.

[Formula on PDF page 2 (7)](../assets/supp_figs/s10-formula-p0002-006.jpg)

[Formula on PDF page 2 (8)](../assets/supp_figs/s10-formula-p0002-007.jpg)

where _E_ and _I_ represent the activity of the excitatory and inhibitory neural populations in the form of mean firing rates, _τe/i_ are the excitatory/inhibitory time constants, _wab_ are the local connection strengths from population _a_ to population _b_ , _P_ is a constant external input to the excitatory neural population, and _ϵ_ is a noise signal added to the system. The studied NMMs share similar parameters, with some variations such as the use of membrane potential instead of firing rates as the state variable, and the concatenation of the external input and noise term into a single variable.

Concurrently to WC and Freeman, Lopes da Silva and colleagues developed a point-process model of EEG alpha rhythm generated with a corticothalamic loop [16]. Specifically, these authors proposed a negative feedback loop between excitatory thalamocortical relay cells and inhibitory thalamic reticular neurons as the basis for generating certain brain rhythms, in a manner similar to the interacting E and I populations in the WC model. By applying linear systems analysis to investigate the influence of physiological parameters on neural periodic patterns, they established a novel approach to studying oscillatory dynamics in theoretical neuroscience that relied on analytical power spectra. The Lopes da Silva model had a substantial impact on subsequent corticothalamic models and linear analysis tools [17,18].

A few years later, Zetterberg et al. (1978) [19] built an extension of the model by adding a second cortical excitatory population in order to separately account for pyramidal cells and excitatory interneurons. Their work was then reprised and further popularized by Jansen and Rit (1995) [20]. In the JR model, each neural population is described in two steps: a transformation of the incoming average pulse density of action potentials into an average postsynaptic membrane potential, followed by a sigmoidal function to perform the inverse conversion. Over the years, several extended versions of JR have been proposed [21–24], - including Moran et al., where they focused on steady-state spectral responses with a linearized approximation of the model [25]. Contemporaneous with these early conceptualizations and formulations of NMMs in the 1970s was the introduction of NFMs by Amari, Wilson & Cowan, Nunez, and others. The ‘brain wave equation’ model of [26] is particularly important here as it was the first to attempt to describe neural activity across the entire cerebral cortex with an evolution in both time and space. This work was a major influence for several macroscale NFM formulations in the 1990s [27–29]. The latter of these which was then extended in 2001 to include the thalamus, and subsequently used to investigate a wide range of brain states including sleep [30,31], epileptic seizures [32,33], evoked responses [34], functional connectivity [35], and alpha rhythms [30,36].

For a more detailed timeline and review on the development of NPMs and whole brain modelling in general, we refer the reader to Griffiths et al. (2022) [37] and Chow et al. (2020) [10]. The early mathematical models reviewed there and above laid the groundwork for most NPM formulations used in theoretical neuroscience today. In particular, they form the basis for the four most widely studied models of the EEG alpha rhythm - Jansen-Rit (JR), Moran-David-Friston (MDF), Liley-Wright (LW) and Robinson-Rennie-Wright (RRW).

### Pacemaker vs. Local Network vs. Global Network Alpha theories

As indicated in the main text, the theories of alpha in the literature can be grouped under three categories: _pacemaker_ , _local network_ , and _global network_ theories. For reasons of space we discuss only the second of these in this article. The following provide some further notes and references for the interested reader on the other two. The pacemaker theory suggests that intrinsic alpha oscillations are generated either in the thalamus, driven by pulvinar or and/or the lateral geniculate nucleus [38–40] or in the cortex, originating from the pyramidal cells located in layer V [41–43]. However, pacemaker theories in general suffer from several severe limitations (see Nunez (2006) [44] for an extensive discussion of this). For instance, pacemaker cells such as putative thalamic nuclei, if they exist, would have to function in a relatively autonomous fashion, having a highly restricted input from other oscillatory brain regions - a notion that has been critically questioned on anatomical grounds [45,46]. Additionally, there are certain global EEG phenomena that remain unexplained, including the relative frequencies of major rhythms and sleep-wave variations. The second category, ‘local network’ theories, propose that alpha rhythms are produced by interactions between excitatory and inhibitory neural populations with dendritic response functions and saturating nonlinearities [47]. Finally, ‘global network’ theories posit that alpha rhythms are generated by large-scale networks rather than local circuits within a localized brain region. By disregarding complex dendritic response functions and finite intracortical propagation, models with a primary emphasis on global dynamics rely heavily on the propagation delays between distant anatomical structures to shape their dynamics [47–49].

### References

- [1] Beurle RL. Properties of a mass of cells capable of regenerating pulses. Philosophical Transactions of the Royal Society of London Series B, Biological Sciences. 1956; p. 55–94.

- [2] Griffith JS. A field theory of neural nets: I: Derivation of field equations. The bulletin of mathematical biophysics. 1963;25:111–120.

- [3] Freeman WJ. Linear analysis of the dynamics of neural masses. Annual review of biophysics and bioengineering. 1972;1(1):225–256.

- [4] Freeman WJ. Waves, pulses, and the theory of neural masses. Progress in theoretical biology. 1972;2(1):1–10.

- [5] Freeman WJ. Mass action in the nervous system. vol. 2004. Citeseer; 1975.

- [6] Deschle N, Ignacio Gossn J, Tewarie P, Schelter B, Daffertshofer A. On the validity of neural mass models. Frontiers in computational neuroscience. 2021; p. 118.

- [7] Freeman WJ. Nonlinear gain mediating cortical stimulus-response relations. Biological cybernetics. 1979;33(4):237–247.

- [8] Wilson HR, Cowan JD. Excitatory and inhibitory interactions in localized populations of model neurons. Biophysical journal. 1972;12(1):1–24.

- [9] Destexhe A, Sejnowski TJ. The Wilson–Cowan model, 36 years later. Biological cybernetics. 2009;101(1):1–2.

- [10] Chow CC, Karimipanah Y. Before and beyond the Wilson–Cowan equations. Journal of neurophysiology. 2020;123(5):1645–1656.

- [11] Kilpatrick ZP. In: Jaeger D, Jung R, editors. Wilson-Cowan Model. New York, NY: Springer New York; 2013. p. 1–5. Available from: https://doi.org/10.1007/978-1-4614-7320-6_80-1.

- [12] Sanz-Leon P, Knock SA, Spiegler A, Jirsa VK. Mathematical framework for large-scale brain network modeling in The Virtual Brain. Neuroimage. 2015;111:385–430.

- [13] Nakagawa TT, Woolrich M, Luckhoo H, Joensson M, Mohseni H, Kringelbach ML, et al. How delays matter in an oscillatory whole-brain spiking-neuron network model for MEG alpha-rhythms at rest. Neuroimage. 2014;87:383–394.

- [14] Cowan JD, Neuman J, van Drongelen W. Wilson–Cowan equations for neocortical dynamics. The Journal of Mathematical Neuroscience. 2016;6(1):1–24.

- [15] Abeysuriya RG, Hadida J, Sotiropoulos SN, Jbabdi S, Becker R, Hunt BA, et al. A biophysical model of dynamic balancing of excitation and inhibition in fast oscillatory large-scale networks. PLoS computational biology. 2018;14(2):e1006007.

- [16] Lopes da Silva F, Hoeks A, Smits H, Zetterberg L. Model of brain rhythmic activity. Kybernetik. 1974;15(1):27–37.

- [17] Cona F, Lacanna M, Ursino M. A thalamo-cortical neural mass model for the simulation of brain rhythms during sleep. Journal of Computational Neuroscience. 2014;37(1):125–148.

- [18] Bhattacharya BS, Coyle D, Maguire LP. A thalamo–cortico–thalamic neural mass model to study alpha rhythms in Alzheimer’s disease. Neural networks. 2011;24(6):631–645.

- [19] Zetterberg LH, Kristiansson L, Mossberg K. Performance of a model for a local neuron population. Biological cybernetics. 1978;31(1):15–26.

- [20] Jansen BH, Rit VG. Electroencephalogram and visual evoked potential generation in a mathematical model of coupled cortical columns. Biological cybernetics. 1995;73(4):357–366.

- [21] Wendling F, Bellanger JJ, Bartolomei F, Chauvel P. Relevance of nonlinear lumped-parameter models in the analysis of depth-EEG epileptic signals. Biological cybernetics. 2000;83(4):367–378.

- [22] David O, Friston KJ. A neural mass model for MEG/EEG:: coupling and neuronal dynamics. NeuroImage. 2003;20(3):1743–1755.

- [23] Zavaglia M, Astolfi L, Babiloni F, Ursino M. A neural mass model for the simulation of cortical activity estimated from high resolution EEG during cognitive or motor tasks. Journal of neuroscience methods. 2006;157(2):317–329.

- [24] Sotero RC, Trujillo-Barreto NJ, Iturria-Medina Y, Carbonell F, Jimenez JC. Realistically coupled neural mass models can generate EEG rhythms. Neural computation. 2007;19(2):478–512.

- [25] Moran RJ, Kiebel SJ, Stephan KE, Reilly R, Daunizeau J, Friston KJ. A neural mass model of spectral responses in electrophysiology. NeuroImage. 2007;37(3):706–720.

- [26] Nunez PL. The brain wave equation: a model for the EEG. Mathematical Biosciences. 1974;21(3-4):279–297.

- [27] Jirsa VK, Haken H. Field theory of electromagnetic brain activity. Physical review letters. 1996;77(5):960.

- [28] Wright J, Liley D. Dynamics of the brain at global and microscopic scales: Neural networks and the EEG. Behavioral and Brain Sciences. 1996;19(2):285–295.

- [29] Robinson PA, Rennie CJ, Wright JJ. Propagation and stability of waves of electrical activity in the cerebral cortex. Physical Review E. 1997;56(1):826.

- [30] Robinson PA, Rennie C, Rowe DL, O’Connor S, Gordon, E. Multiscale brain modelling. Philosophical Transactions of the Royal Society B: Biological Sciences. 2005;360(1457):1043–1050.

- [31] Abeysuriya RG, Rennie CJ, Robinson PA. Prediction and verification of nonlinear sleep spindle harmonic oscillations. Journal of Theoretical Biology. 2014;344:70–77.

- [32] Breakspear M, Roberts JA, Terry JR, Rodrigues S, Mahant N, Robinson PA. A unifying explanation of primary generalized seizures through nonlinear brain modeling and bifurcation analysis. Cerebral Cortex. 2006;16(9):1296–1313.

- [33] Zhao X, Robinson PA. Generalized seizures in a neural field model with bursting dynamics. Journal of computational neuroscience. 2015;39(2):197–216.

- [34] Kerr CC, Rennie CJ, Robinson PA. Physiology-based modeling of cortical auditory evoked potentials. Biological cybernetics. 2008;98:171–184.

- [35] Robinson P. Determination of effective brain connectivity from functional connectivity using propagator-based interferometry and neural field theory with application to the corticothalamic system. Physical Review E. 2014;90(4):042712.

- [36] Robinson P, Rennie C, Rowe D. Dynamics of large-scale brain activity in normal arousal states and epileptic seizures. Physical Review E. 2002;65(4):041924.

- [37] Griffiths JD, Bastiaens SP, Kaboodvand N. Whole-Brain Modelling: Past, Present, and Future. In: Computational Modelling of the Brain. Springer; 2022. p. 313–355.

- [38] Saalmann YB, Pinsk MA, Wang L, Li X, Kastner S. The pulvinar regulates information transmission between cortical areas based on attention demands. science. 2012;337(6095):753–756.

- [39] Lőrincz ML, Kékesi KA, Juhász G, Crunelli V, Hughes SW. Temporal framing of thalamic relay-mode firing by phasic inhibition during the alpha rhythm. Neuron. 2009;63(5):683–696.

- [40] Hughes SW, Lőrincz ML, Blethyn K, Kékesi KA, Juhász G, Turmaine M, et al. Thalamic gap junctions control local neuronal synchrony and influence macroscopic oscillation amplitude during EEG alpha rhythms. Frontiers in psychology. 2011;2:193.

- [41] Lopes da Silva F. Neural mechanisms underlying brain waves: from neural membranes to networks. Electroencephalography and clinical neurophysiology. 1991;79(2):81–93.

- [42] Connors BW, Amitai Y. Making waves in the neocortex. Neuron. 1997;18(3):347–349.

- [43] Bollimunta A, Chen Y, Schroeder CE, Ding M. Neuronal mechanisms of cortical alpha oscillations in awake-behaving macaques. Journal of Neuroscience. 2008;28(40):9976–9988.

- [44] Nunez PL, Srinivasan R, et al. Electric fields of the brain: the neurophysics of EEG. Oxford University Press, USA; 2006.

- [45] Lopes da Silva F. Dynamics of EEGs as signals of neuronal populations: models and theoretical considerations. Electroencephalography: Basic Principles, Clinical Applications and Related Fields, 4th edition. 1998; p. 76–92.

- [46] Steriade M. Cellular substrates of brain rhythms. Electroencephalography: Basic principles, clinical applications, and related fields. 2005;5:31–83.

- [47] Valdés-Hernández PA, Ojeda-González A, Martínez-Montes E, Lage-Castellanos A, Virués-Alba T, Valdés-Urrutia L, et al. White matter architecture rather than cortical surface area correlates with the EEG alpha rhythm. Neuroimage. 2010;49(3):2328–2339.

- [48] Nunez PL, Cutillo BA. Neocortical dynamics and human EEG rhythms. Oxford University Press, USA; 1995.

- [49] Nunez PL, Srinivasan R. A theoretical basis for standing and traveling brain waves measured with human EEG with implications for an integrated consciousness. Clinical neurophysiology. 2006;117(11):2424–2435.

## Conversion notes

- Page 2 item p0002-b009 reads 'translating equation (40) back into the time domain' — verified against both the high-res preview and raw PDF text-layer evidence that this is genuinely printed as '(40)' in the source PDF (likely a stale cross-reference from the main manuscript's global equation numbering, left over when this appendix's equations were locally renumbered 1-19). Preserved verbatim per source-fidelity policy; this is not a transcription error.
- Cross-page join verified: page 1's last text item (p0001-b019, 'Now, with an expression for H(s) ... and given that y(t) is equal to') continues into page 2's first text item (p0002-b001, 'the convolution of h(t) and x(t) ...'); join_previous='space' is correctly set on p0002-b001.
- All model-specific transfer-function equations (JR, MDF, LW, RRW) are embedded inside composite multi-panel Figure A (page 1) alongside their power-spectrum plots, per the source PDF's layout; they are not extractable as standalone formula items without fragmenting the panel. Captured as a single figure image crop verified complete with no clipping at 3x zoom.
- Page 1 (p0001-b010, 6x6 Jacobian for JR) and page 2 (p0002-b005, 10x10 symbolic + evaluated Jacobian for LW) contain large matrix formulas preserved as image-only formula crops rather than transcribed as text/LaTeX, due to their size and dense sub/superscript notation; verified complete with no clipping at 2.5-6x zoom.
- Page 3's References section (2 entries) was auto-flagged by the table-detector and extracted as a single-column 'table' with embedded margin line-numbers and <br> corruption, but the content is a plain reference list, not tabular data. Reclassified to two clean text/list-item entries (p0003-b002, p0003-b004) rather than kept as a table with image fallback, since the text transcribes cleanly and losslessly.
- Figure A caption (p0001-b011) contains the source document's own typo 'connetivity' (should be 'connectivity') in the B1/B2 sentence; preserved verbatim per source-fidelity policy rather than silently corrected.
- Source inconsistency retained: the central 3D plot title is C3,4 = 33.75, while the caption states C3,4 = 33.5. These are distinct printed values, not a transcription choice.
- All displayed equations (JR eqs 1-6, MDF eqs 7-12, LW eqs 19-28, RRW eqs 29-36) are captured as kind=formula image crops rather than transcribed to LaTeX/markdown text. This is intentional: the source PDF renders these with CM math fonts lacking reliable ToUnicode mapping for many Greek-letter/subscript/superscript glyphs, so image-crop extraction is the only way to preserve full fidelity (correct subscripts, stacked fractions/radicals, embedded (N) equation-number labels) without risking silent corruption. Audited page-by-page (6/6 pages) against evidence + 600 DPI re-renders of source.pdf; one genuine content fix made on page 4 (garbled HTML run-on in prose) and one structural fix on page 6 (a table cell had been mis-represented as a 3-line stacked fraction using a strikethrough-radical hack when the source is actually a single inline run 'sigma-prime * pi * sqrt(3)').
- Table D prints σ′π√3 and 3.8∗π√3 ≈ 5.9 mV; this is retained exactly although the stated arithmetic is inconsistent. Its 1/α and 1/β rows also retain the printed s^−1 units. CSV superscripts use explicit ^(...) notation; subscripts in symbols follow the source's compact plain-text letter convention.
- Audited all 7 pages against evidence + preview images. Two cross-page prose continuations were independently re-verified by eye: (1) page 2 item b010 ('...pyramidal cells and') into page 3 item b006 ('excitatory interneurons. Their work was...') -- genuine sentence continuation, join_previous=space is correct (not a hyphen/word split); (2) page 3 item b009 ('...rely heavily on') into page 4 item b000 ('the propagation delays...') -- also a genuine sentence continuation, join_previous=space is correct. Both were already set correctly by the prior review pass; no changes needed. No content errors found in the reference lists (pages 4-7, 49 citations total) -- checked diacritics, DOIs, and hyphenated surnames/line-wraps against 600 DPI zoomed source.pdf crops where ambiguous.
