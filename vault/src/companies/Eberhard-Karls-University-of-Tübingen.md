```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eberhard-Karls-University-of-Tübingen" or company = "Eberhard Karls University of Tübingen")
sort location, dt_announce desc
```
