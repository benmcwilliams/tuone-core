```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "JLEN-Environmental" or company = "JLEN Environmental")
sort location, dt_announce desc
```
