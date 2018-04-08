#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import libvirt
import commands

def environmentSetup():
    """
    Installs all the required libraries for KVM based VM creation & management on Ubuntu
    """
    os.system("sudo apt-get -y install qemu-kvm")
    os.system("sudo apt-get -y install libvirt-bin")
    os.system("sudo apt-get -y install virt-manager")
    os.system("sudo apt-get -y install virt-viewer")
    os.system("sudo apt-get install python-libvirt")
    os.system("sudo apt-get install libvirt-doc")

def getConnection():
    """
    Opens a connection to the local hypervisor
    :return: connection pointer
    """
    conn = libvirt.open('qemu:///system')
    if conn == None:
        print('Failed to open connection to qemu:///system', file=sys.stderr)
        exit(1)
    else:
        return conn


def listDomInfo(conn):
    """
    :param conn: connection pointer
    lists information about all running domains
    """
    for id in conn.listDomainsID():
        dom = conn.lookupByID(id)
        infos = dom.info()
        print('ID = %d' % id)
        print('Name =  %s' % dom.name())
        print('State = %d' % infos[0])
        print('Max Memory = %d' % infos[1])
        print('Number of virt CPUs = %d' % infos[3])
        print('CPU Time (in ns) = %d' % infos[2])
        print(' ')


def defineNetwork(conn, xmlPath, networkName):
    # create a persistent virtual network
    os.system("brctl addbr %s\nip link set %s up" %(networkName,networkName))
    f = open(xmlPath)
    xmlconfig = f.read()
    network = conn.networkCreateXML(xmlconfig)
    if network == None:
        print('Failed to create a virtual network', file=sys.stderr)
        exit(1)
    active = network.isActive()
    if active == 1:
        print('The new persistent virtual network is active')
    else:
        print('The new persistent virtual network is not active')





def listNetworks(conn):
    """
    List all the virtual networks in the hypervisor
    :param conn: connection pointer
    """
    networks = conn.listNetworks()
    print('Virtual networks:')
    for network in networks:
        print('  ' + network)
    print(' ')

    #### If you need to get list of linux virtual bridges uncomment the below lines
    # status, output = commands.getstatusoutput("brctl show | cut -f1")
    # existing = [x for x in output.split("\n")[1:] if x != '']
    # print(existing)


def defineVM(conn, xmlPath):
    """
    Creates a persistent VM and boots it up
    :param conn: connection pointer
    :param xmlPath: absolute path to xml config file as string
    :return:
    """
    f = open(xmlPath)
    xmlconfig = f.read()
    dom = conn.defineXML(xmlconfig)
    if dom == None:
        print('Failed to define a domain from an XML definition.', file=sys.stderr)
        exit(1)
    if dom.create(dom) < 0:
        print('Can not boot guest domain.', file=sys.stderr)
        exit(1)
    print('Guest '+dom.name()+' has booted', file=sys.stderr)
    f.close()


def main():

    conn = getConnection()
    defineVM(conn,"/home/atandon/sampleVM.xml")




    conn.close()
    exit(0)


if __name__ == "__main__":
    main()

