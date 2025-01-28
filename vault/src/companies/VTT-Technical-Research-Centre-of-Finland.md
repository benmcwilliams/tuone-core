```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "VTT-Technical-Research-Centre-of-Finland" or company = "VTT Technical Research Centre of Finland")
sort location, dt_announce desc
```
