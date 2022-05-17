import Simulation
import time

def main():
    st = time.time()
    sim = Simulation.simulation()
    sim.runSimulations()
    time.sleep(3)
    et = time.time()
    elapsed_time = et - st
    print('CPU time ', elapsed_time)

if __name__ == "__main__":
    main()