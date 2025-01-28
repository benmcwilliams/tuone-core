```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "F&S-Solar" or company = "F&S Solar")
sort location, dt_announce desc
```
