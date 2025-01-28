```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sines-hydrogen-facility" or company = "Sines hydrogen facility")
sort location, dt_announce desc
```
