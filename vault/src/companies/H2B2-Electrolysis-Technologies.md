```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "H2B2-Electrolysis-Technologies" or company = "H2B2 Electrolysis Technologies")
sort location, dt_announce desc
```
