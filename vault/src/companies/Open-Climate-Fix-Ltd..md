```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Open-Climate-Fix-Ltd." or company = "Open Climate Fix Ltd.")
sort location, dt_announce desc
```
