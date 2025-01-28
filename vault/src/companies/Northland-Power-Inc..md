```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Northland-Power-Inc." or company = "Northland Power Inc.")
sort location, dt_announce desc
```
