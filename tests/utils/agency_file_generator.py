def generate(filepath, bet_amount):
    with open(filepath, "w") as agency_file:
        for i in range(bet_amount):
            agency_file.write(f"A,B,{str(i).zfill(8)},2000-01-01,{i}\n")
        agency_file.flush()
