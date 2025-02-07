```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Photowatt-International" or company = "Photowatt International")
sort location, dt_announce desc
```
