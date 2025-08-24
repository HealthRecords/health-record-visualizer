

data = """
          { year: 2010, value: 10 },
            { year: 2011, value: 20 },
            { year: 2012, value: 15 },
            { year: 2013, value: 25 },
            { year: 2014, value: 30 },
            { year: 2015, value: 35 },
            { year: 2016, value: 40 },
            { year: 2017, value: 45 },
            { year: 2018, value: 50 },
            { year: 2019, value: 55 }
"""

if __name__ =='__main__':
    with open("d3_template.html") as f:
        template = f.read()
    output = template.replace("{{ data }}", data )
    with open("output/d3_example.html", "w") as f:
        f.write(output)