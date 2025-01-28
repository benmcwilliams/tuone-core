```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Scatec-Solar-ASA" or company = "Scatec Solar ASA")
sort location, dt_announce desc
```
