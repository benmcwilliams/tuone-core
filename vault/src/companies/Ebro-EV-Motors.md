```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ebro-EV-Motors" or company = "Ebro EV Motors")
sort location, dt_announce desc
```
