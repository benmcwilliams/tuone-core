```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Helen-Ltd" or company = "Helen Ltd")
sort location, dt_announce desc
```
