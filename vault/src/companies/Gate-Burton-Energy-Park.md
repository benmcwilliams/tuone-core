```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gate-Burton-Energy-Park" or company = "Gate Burton Energy Park")
sort location, dt_announce desc
```
