```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "French Alternative Energies and Atomic Energy Commission"
sort location, dt_announce desc
```
