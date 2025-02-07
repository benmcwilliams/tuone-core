```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Utility-Scale-PV" or company = "Utility Scale PV")
sort location, dt_announce desc
```
