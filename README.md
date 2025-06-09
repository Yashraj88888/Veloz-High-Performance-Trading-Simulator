# Veloz : High Perfoamnce Digital Assets Trading Simulator
This particular trading simulator is built for the purpose of demonstrating market order trade execution of digital assets like Bitcoin-USD, Ethereum, etc and it's impact on market, liquidity profile(maker/taker), fees and net cost of trade at each timestamp at ultra low latency.

The entire simulator is built using python and implements:
1. Linear Regression (slippage calculation)
2. Logistic Regression (maker/taker)
3. Gatheral's Non-Linear Market Impact model (market Impact)

![Veloz1](https://github.com/user-attachments/assets/eefce947-77fc-42c0-9461-d7d1f7787eea)





### File Structure
<img width="838" alt="image" src="https://github.com/user-attachments/assets/f11afef6-f1bf-4c22-8a58-c94ef204938c" />

### Setup and Installation
1. The simulator is built using python in conda environment.
2. Install Anaconda or Miniconda on your pc through browser.
3. Extract the zip file and locate the files on appropriate location on your pc.
4. Setup conda environment by opening the terminal or Anaconda prompt and navigating
to the path to the folder named “Trading_simulator”, using :
* cd path/to/rootsimulatorfolder (replace with actual path) *
5. Run the following command to create the environment:
conda env create -f environment.yml
6. Activate the environment using:
* conda activate base (“base” is the name written in environment.yml file on the first line) *
7. Install all the required packages mentioned in yml file manually in case of missing packages.
8. First you need to scrape and build CSV files for slippage history and maker/taker history. So, Go to scripts/ and run the two python files (build_makertaker_history.py and buil_slippage_history.py) which will create the two required CSV files.
9. Then, train the regression models on the historical data fetched in CSV files. For that, Go to models/ and run the two files (train_maker_taker.py and train_slippage_model.py) individually whihc will create two .pkl files required futher for calculations.
8. Now after the above steps have been completed and the files have been created, Run the command:
* python main.py (main.py is the entry point) *
