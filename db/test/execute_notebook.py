#!/usr/bin/env python3
"""Execute OMOPHub_Workflow_Demonstration.ipynb and embed outputs."""

import io
import sys
import json
import base64
import contextlib
import traceback
from pathlib import Path
import nbformat as nbf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display

def run_notebook(nb_path: str):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbf.read(f, as_version=4)

    global_ns = {
        '__name__': '__main__',
        'display': lambda obj: global_ns['_captured_displays'].append(obj),
        '_captured_displays': []
    }

    print(f"Executing {len(nb.cells)} cells...")
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != 'code':
            continue

        source = cell.source
        print(f"--- Running Cell {idx} ---")
        
        # Capture stdout and stderr
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        global_ns['_captured_displays'] = []
        plt.close('all')

        cell_outputs = []

        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                # Execute the cell
                exec(source, global_ns)
                
            stdout_str = stdout_buf.getvalue()
            stderr_str = stderr_buf.getvalue()

            if stdout_str:
                cell_outputs.append(nbf.v4.new_output(
                    output_type='stream',
                    name='stdout',
                    text=stdout_str
                ))

            if stderr_str:
                cell_outputs.append(nbf.v4.new_output(
                    output_type='stream',
                    name='stderr',
                    text=stderr_str
                ))

            # Check if any displays were captured (e.g. DataFrames)
            for disp in global_ns.get('_captured_displays', []):
                if hasattr(disp, 'to_html'):
                    html_data = disp.to_html()
                    text_data = repr(disp)
                    cell_outputs.append(nbf.v4.new_output(
                        output_type='display_data',
                        data={
                            'text/html': html_data,
                            'text/plain': text_data
                        },
                        metadata={}
                    ))
                elif isinstance(disp, str):
                    cell_outputs.append(nbf.v4.new_output(
                        output_type='display_data',
                        data={'text/plain': disp},
                        metadata={}
                    ))

            # Check if there is an active matplotlib figure
            figs = [plt.figure(n) for n in plt.get_fignums()]
            for fig in figs:
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=120)
                img_buf.seek(0)
                img_b64 = base64.b64encode(img_buf.read()).decode('utf-8')
                cell_outputs.append(nbf.v4.new_output(
                    output_type='display_data',
                    data={
                        'image/png': img_b64,
                        'text/plain': '<Figure size ...>'
                    },
                    metadata={}
                ))
            plt.close('all')

            cell.outputs = cell_outputs
            cell.execution_count = idx
            print(f" Cell {idx} completed with {len(cell_outputs)} outputs.")

        except Exception as e:
            err_msg = traceback.format_exc()
            print(f"❌ Error in Cell {idx}: {e}")
            print(err_msg)
            cell.outputs = [
                nbf.v4.new_output(
                    output_type='error',
                    ename=type(e).__name__,
                    evalue=str(e),
                    traceback=err_msg.splitlines()
                )
            ]
            break

    with open(nb_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    print(f" Successfully executed and updated {nb_path}!")

if __name__ == '__main__':
    run_notebook('/mnt/bucket/BioLink/db/test/OMOPHub_Workflow_Demonstration.ipynb')
