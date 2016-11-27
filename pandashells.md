Pandashells One-liner Example
===

<a href="https://github.com/robdmc/pandashells">Pandashells</a> lets you use <a
href="http://pandas.pydata.org/">Pandas</a> from the bash command line.  It
allows you to combine unix command-line tools (awk, grep, sed, etc.) with the
power of Pandas Dataframes and Matplotlib visualization.

Here is a one-liner that performs the exact same aggregation demonstrated by the
example consecution pipeline.

```bash
cat sample_data.csv | \
p.df 'df["group"] = ["adult" if a>=18 else "child" for a in df.age]' | \
p.df 'df.pivot_table(index="group", columns="gender", values="spent", margins=True, aggfunc=sum).fillna(0)' \
-o table index
```
