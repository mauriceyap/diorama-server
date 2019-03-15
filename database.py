from tinydb import TinyDB

programs_db: TinyDB = TinyDB('out/programs_db.json')
network_topology_db: TinyDB = TinyDB('out/network_topology_db.json')
custom_config_db: TinyDB = TinyDB('out/custom_config_db.json')
simulation_db: TinyDB = TinyDB('out/simulation_db.json')
