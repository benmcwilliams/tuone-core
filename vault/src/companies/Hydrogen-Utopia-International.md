```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hydrogen-Utopia-International" or company = "Hydrogen Utopia International")
sort location, dt_announce desc
```
