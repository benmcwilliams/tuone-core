```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Orkustofnun" or company = "Orkustofnun")
sort location, dt_announce desc
```
