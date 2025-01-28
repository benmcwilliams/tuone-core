```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Jóvenes-Nucleares" or company = "Jóvenes Nucleares")
sort location, dt_announce desc
```
