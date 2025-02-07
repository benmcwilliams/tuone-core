```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "3megawatt" or company = "3megawatt")
sort location, dt_announce desc
```
