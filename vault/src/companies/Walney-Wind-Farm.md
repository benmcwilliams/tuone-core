```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Walney-Wind-Farm" or company = "Walney Wind Farm")
sort location, dt_announce desc
```
