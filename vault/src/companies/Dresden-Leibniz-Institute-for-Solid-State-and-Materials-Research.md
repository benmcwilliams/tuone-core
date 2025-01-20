```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Dresden Leibniz Institute for Solid State and Materials Research"
sort location, dt_announce desc
```
