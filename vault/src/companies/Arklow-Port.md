```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Arklow-Port" or company = "Arklow Port")
sort location, dt_announce desc
```
