```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Copenhagen-Infrastructure-Partners-(CIP)" or company = "Copenhagen Infrastructure Partners (CIP)")
sort location, dt_announce desc
```
