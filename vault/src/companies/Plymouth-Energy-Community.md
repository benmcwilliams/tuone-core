```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Plymouth-Energy-Community" or company = "Plymouth Energy Community")
sort location, dt_announce desc
```
