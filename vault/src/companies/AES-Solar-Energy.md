```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "AES-Solar-Energy" or company = "AES Solar Energy")
sort location, dt_announce desc
```
