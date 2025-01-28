```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Xing-Mobility" or company = "Xing Mobility")
sort location, dt_announce desc
```
