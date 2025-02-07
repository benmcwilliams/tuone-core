```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "British-Gas" or company = "British Gas")
sort location, dt_announce desc
```
