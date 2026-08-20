def generate(filepath, register_amount):
    lines = []

    for i in range(register_amount):
        lines.append(f"A,B,{str(i).zfill(8)},2000-01-01,{i}\n")

    with open(filepath, "w") as file:
        file.write("".join(lines))
