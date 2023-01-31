import statistics, csv


def print_stats(path):
    goals, edges, paths = [], [], []

    with open(path) as f:
        r = csv.reader(f)
        for row in r:
            goals.append(int(row[0]))
            edges.append(int(row[1]))
            paths.append(int(row[2]))

    def print_stats(label, data):
        med = int(statistics.median(data))
        var = statistics.variance(data)
        m = max(data)
        print(f"{label}: max {m}, median {med}, variance {var}")

    print(f'-- {path} --')
    print_stats("Goals", goals)
    print_stats("Edges", edges)
    print_stats("Paths", paths)


print_stats('unit_stats.csv')
print_stats('properties_stats_dev.csv')
print_stats('properties_stats_ci.csv')
print_stats('properties_stats_stateful_dev.csv')
print_stats('properties_stats_stateful_ci.csv')
print_stats('real_stats.csv')
