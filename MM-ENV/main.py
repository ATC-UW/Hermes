from simulation import Simulation
from maker import SimpleMarketMaker as MarketMaker

def main():
    print("Welcome to the game!")
    mm = MarketMaker()
    sim = Simulation(mm)
    sim.run(logging=True)
    sim.summarize(logging=True)
    

if __name__ == "__main__":
    main()