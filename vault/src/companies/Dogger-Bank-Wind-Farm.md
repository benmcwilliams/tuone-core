```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dogger-Bank-Wind-Farm" or company = "Dogger Bank Wind Farm")
sort location, dt_announce desc
```
